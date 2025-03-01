from model import *
from data import *
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence
import sys
import json

INPUT_FILE_PATH = './test_short.jsonl'
OUTPUT_PATH = './output.jsonl'
MODEL_PATH = './best.pt'
INDEX2WORD_PATH = './model/index2word.pt'
INDEX2VEC_PATH = './model/index2vec.pt'
predict_batch_size = 5

def evaluate(seq2seq, batch, index2vec):
    with torch.no_grad():
        x_padded, x_len, idx = batch
        x_padded.to(DEVICE)

        decoder_output, hidden = seq2seq.predict((x_padded, x_len), index2vec)

        topv, topi = torch.topk(decoder_output, 1)
        outputs = topi.squeeze(2).transpose(0, 1).contiguous()

        return outputs, idx

def main(model_path=MODEL_PATH, input_file_path=INPUT_FILE_PATH, output_path=OUTPUT_PATH):

    #create predicting dataset and dataloader
    predicting_dataset = ArticleDataset(input_file_path, predicting=True)
    predicting_data_loader = DataLoader(predicting_dataset, batch_size=predict_batch_size, shuffle=False)

    #load the model
    seq2seq = torch.load(model_path, map_location=torch.device('cpu'))
    index2word = torch.load(INDEX2WORD_PATH, map_location=torch.device('cpu'))
    index2vec = torch.load(INDEX2VEC_PATH, map_location=torch.device('cpu'))

    #if gpu is available
    seq2seq = seq2seq.to(DEVICE)



    output_list = []

    for i_batch, batch in enumerate(predicting_data_loader):

        #no need to backprop, so no_grad
        outputs, idx = evaluate(seq2seq, batch, index2vec)
        for i, output in enumerate(outputs):
            output_str = []
            for word in output:
                if word.item() == EOS_ID:
                    break
                output_str += [index2word.index2word[word.item()]]
            output_list += ['\"id\": \"{}\", \"predict\": \"{}\"'.format(predicting_dataset.article(idx[i]).id, ' '.join(output_str))]
            print(output_list[-1])
        print('batch {} complete'.format(i_batch))

    with open(output_path, 'w') as output_file:
        for output in output_list:
            output_file.write('{' + output + '}\n')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        main()
    elif len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print('usage: python predict.py [model path] [input file path] [output file path]')
        print('if path not assigned, model path: {}, input file path: {}, output file path: {}'.format(MODEL_PATH, INPUT_FILE_PATH, OUTPUT_PATH))
        exit()
